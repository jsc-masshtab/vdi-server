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
        PRJNAME = "veil-broker-backend"
        NFS_DIR = "/nfs/vdi-deb"
        DEB_ROOT = "${WORKSPACE}/devops/deb"
        DATE = "${currentDate}"
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
        string(    name: 'BRANCH',         defaultValue: branch,          description: 'branch')
        choice(    name: 'REPO',           choices: repos,                description: 'repo for uploading')
        string(    name: 'VERSION',        defaultValue: version,         description: 'base version')
        choice(    name: 'AGENT',          choices: agents,               description: 'jenkins build agent')
        string(    name: 'BROKER_NAME',    defaultValue: 'VeiL VDI',      description: 'broker name')
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
                    sed -i "s:%%VER%%:${VERSION}-${BUILD_NUMBER}:g" "${DEB_ROOT}/${PRJNAME}/root/DEBIAN/control"

                    mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
                    rsync -a ${WORKSPACE}/backend/ "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"

                    # create virtual env
                    /usr/bin/python3 -m virtualenv ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env
                    # install requirements
                    cd ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app
                    ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env/bin/python -m pip --no-cache-dir install -r requirements.txt
                    # set BROKER_NAME
                    echo "BROKER_NAME = \\"${BROKER_NAME}\\"" > common/broker_name.py
                    # make relocatable env
                    virtualenv --relocatable ../env

                    # compilemessages
                    cd common
                    chmod +x compilemessages.sh
                    ./compilemessages.sh en
                    ./compilemessages.sh ru
                    cd ..

                    # build deb
                    make -C "${DEB_ROOT}/${PRJNAME}"

                    # upload to nfs
                    mkdir -p ${NFS_DIR}
                    rm -f ${NFS_DIR}/${PRJNAME}*.deb
                    cp "${DEB_ROOT}/${PRJNAME}"/*.deb ${NFS_DIR}/
                '''
            }
        }

        stage ('publish to repo') {
            steps {
                script {
                    buildSteps.deployToAptly()
                }
            }
        }
    }
}