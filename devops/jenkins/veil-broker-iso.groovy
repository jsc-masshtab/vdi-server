library "vdi-server-libraries@$BRANCH"

def currentDate = new Date().format('yyyyMMddHHmmss')
def branch = buildParameters.branch()
def repos = buildParameters.repos()
def version = buildParameters.version()
def agents = buildParameters.agents()

notifyBuild("STARTED")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        APT_SRV = "192.168.11.118"
        DATE = "${currentDate}"
        ISO_NAME = "veil-broker-${REPO}-${VERSION}-${DATE}-${BUILD_NUMBER}"
        NEXUS_DOCKER_REGISTRY = "nexus.bazalt.team"
        NEXUS_CREDS = credentials('nexus-jenkins-creds')
        DOCKER_IMAGE_NAME = "${NEXUS_DOCKER_REGISTRY}/vdi-builder"
    }

    post {
        always {
            script {
                notifyBuild(currentBuild.result)
            }
        }
    }

    options {
        skipDefaultCheckout(true)
        buildDiscarder(logRotator(daysToKeepStr: '60', numToKeepStr: '100'))
        gitLabConnection('gitlab')
        timestamps()
        ansiColor('xterm')
        parallelsAlwaysFailFast()
    }

    parameters {
        string(    name: 'BRANCH',     defaultValue: branch,     description: 'branch')
        choice(    name: 'REPO',       choices: repos,           description: 'repo for uploading')
        string(    name: 'VERSION',    defaultValue: version,    description: 'base version')
        choice(    name: 'AGENT',      choices: agents,          description: 'jenkins build agent')
    }

    stages {
        stage ('checkout') {
            steps {
                script {
                    buildSteps.gitCheckout("$BRANCH")
                }
            }
        }

        stage('prepare build image') {
            steps {
                script {
                    buildSteps.prepareBuildImage()
                }
            }
        }

        stage('add docker images') {
            steps {
                sh script: '''
                    mkdir -p iso/docker
                    for IMAGE in "postgres:11-alpine" "redis:5-alpine" "nexus.bazalt.team/veil-broker-backend:latest" "nexus.bazalt.team/veil-broker-frontend:latest" "guacamole/guacd:1.3.0"
                    do
                        docker pull $IMAGE
                    done
                    docker save postgres:11-alpine | gzip > iso/docker/postgres.tar.gz
                    docker save redis:5-alpine | gzip > iso/docker/redis.tar.gz
                    docker save nexus.bazalt.team/veil-broker-backend:latest | gzip > iso/docker/backend.tar.gz
                    docker save nexus.bazalt.team/veil-broker-frontend:latest | gzip > iso/docker/frontend.tar.gz
                    docker save guacamole/guacd:1.3.0 | gzip > iso/docker/guacamole.tar.gz
                '''
            }
        }

        stage ('build iso') {
            agent {
                docker {
                    image "${DOCKER_IMAGE_NAME}:${VERSION}"
                    args '-u root:root -v /nfs:/nfs'
                    reuseNode true
                    label "${AGENT}"
                }
            }

            steps {
                sh script: '''
                    # download apt repo
                    wget -r -nH -nv --reject="index.html*" http://${APT_SRV}/veil-broker-${REPO}/
                    mv veil-broker-${REPO}/ iso/repo

                    # copy files
                    cp -r devops/ansible iso/ansible
                    cp devops/installer/install.sh iso

                    # build iso
                    genisoimage -o ./${ISO_NAME}.iso -V veil-broker-${REPO} -R -J ./iso
                '''
            }
        }

        stage ('publish to repo') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'uploader_ssh_key.id_rsa', keyFileVariable: 'SSH_KEY')]) {
                    sh script: '''
                        ssh -o StrictHostKeyChecking=no -i $SSH_KEY uploader@192.168.10.144 "
                            mkdir -p /local_storage/veil-broker-iso/${REPO}
                            rm -f /local_storage/veil-broker-iso/${REPO}/veil-broker-${REPO}-${VERSION}-*.iso
                        "
                        scp -o StrictHostKeyChecking=no -i $SSH_KEY ${ISO_NAME}.iso uploader@192.168.10.144:/local_storage/veil-broker-iso/${REPO}
                    '''
                }
            }
        }
    }
}