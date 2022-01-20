def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

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
        failure {
            println "Something goes wrong"
            println "Current build marked as ${currentBuild.result}"
            notifyBuild(rocketNotify,":x: FAILED", "Something goes wrong. Version: ${currentDate}")
        }

        aborted {
            println "Build was interrupted manually"
            println "Current build marked as ${currentBuild.result}"
            notifyBuild(rocketNotify,":x: FAILED", "Build was interrupted manually. Version: ${currentDate}")
        }

        success {
            notifyBuild(rocketNotify, ":white_check_mark: SUCCESSFUL","Build SUCCESSFUL. Version: ${currentDate}")
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
        string(name: 'BRANCH',  defaultValue: 'dev',                            description: 'branch')
        choice(name: 'REPO',    choices: ['test', 'dev', 'prod-30', 'prod-31'], description: 'repo for uploading')
        string(name: 'VERSION', defaultValue: '3.1.3',                          description: 'base version')
        choice(name: 'AGENT',   choices: ['cloud-ubuntu-20', 'bld-agent'],      description: 'jenkins build agent')
    }

    stages {
        stage ('checkout') {
            steps {
                cleanWs()
                checkout([ $class: 'GitSCM',
                    branches: [[name: '$BRANCH']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [], submoduleCfg: [],
                    userRemoteConfigs: [[credentialsId: 'jenkins-vdi-token',
                    url: 'http://gitlab.bazalt.team/vdi/vdi-server.git']]
                ])
            }
        }

        stage('prepare build image') {
            steps {
                sh script: '''
                    echo -n $NEXUS_CREDS_PSW | docker login -u $NEXUS_CREDS_USR --password-stdin $NEXUS_DOCKER_REGISTRY
                    docker pull $DOCKER_IMAGE_NAME:latest || true
                    cd devops/docker/builder
                    docker build . --pull --cache-from $DOCKER_IMAGE_NAME:latest --tag $DOCKER_IMAGE_NAME:$VERSION
                    docker push $DOCKER_IMAGE_NAME:$VERSION
                    docker tag $DOCKER_IMAGE_NAME:$VERSION $DOCKER_IMAGE_NAME:latest
                    docker push $DOCKER_IMAGE_NAME:latest
                '''
            }
        }

        stage ('build') {
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
                    mkdir iso
                    wget -r -nH -nv --reject="index.html*" http://${APT_SRV}/veil-broker-${REPO}/
                    mv veil-broker-${REPO}/ iso/repo

                    # copy files
                    cp -r devops/ansible iso/ansible
                    rm -f iso/ansible/*.png iso/ansible/*.md iso/ansible/LICENSE
                    cp devops/installer/install.sh iso

                    # build iso
                    genisoimage -o ./${ISO_NAME}.iso -V veil-broker-${REPO} -R -J ./iso

                    # copy iso to nfs
                    mkdir -p /nfs/veil-broker-iso
                    cp ${ISO_NAME}.iso /nfs/veil-broker-iso
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
                        scp -o StrictHostKeyChecking=no -i $SSH_KEY /nfs/veil-broker-iso/${ISO_NAME}.iso uploader@192.168.10.144:/local_storage/veil-broker-iso/${REPO}
                        rm -f /nfs/veil-broker-iso/${ISO_NAME}.iso
                    '''
                }
            }
        }
    }
}

def notifyBuild(rocketNotify, buildStatus, msg) {
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    def summary = "${buildStatus}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})" + "\n"

    summary += "${msg}"

    if (rocketNotify){
        rocketSend (channel: 'jenkins-notify', message: summary, serverUrl: '192.168.14.210', trustSSL: true, rawMessage: true)
    }
}