def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

pipeline {
    agent {
        label "${AGENT}"
    }
    
    environment {
        APT_SRV = "192.168.11.118"
        PRJNAME = "veil-broker-backend"
        NFS_DIR = "/nfs/vdi-deb"
        DEB_ROOT = "${WORKSPACE}/devops/deb"
        DATE = "${currentDate}"
        VER = "${VERSION}-${BUILD_NUMBER}"
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
        string(    name: 'BRANCH',      defaultValue: 'dev',                                                     description: 'branch')
        choice(    name: 'REPO',        choices: ['dev', 'prod-30', 'prod-31', 'prod-32', 'prod-40', 'prod-41'], description: 'repo for uploading')
        string(    name: 'VERSION',     defaultValue: '4.1.0',                                                   description: 'base version')
        choice(    name: 'AGENT',       choices: ['cloud-ubuntu-20', 'bld-agent'],                               description: 'jenkins build agent')
        string(    name: 'BROKER_NAME', defaultValue: 'VeiL VDI',                                                description: 'broker name')
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
                sh script: '''
                    # remove old debs
                    curl -s "http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/packages?q=${PRJNAME}" | jq -r '.[]' | while read KEY;
                    do
                        curl -X DELETE -H 'Content-Type: application/json' -d '{\"PackageRefs\":[\"'"$KEY"'\"]}' http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/packages
                    done

                    # deploy new deb
                    DISTR=1.7_x86-64
                    DEB=$(ls -1 "${DEB_ROOT}/${PRJNAME}"/*.deb)
                    curl -sS -X POST -F file=@$DEB http://$APT_SRV:8008/api/files/veil-broker-${REPO}; echo ""
                    curl -sS -X POST http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/file/veil-broker-${REPO}?forceReplace=1
                    JSON1="{\\"Name\\":\\"veil-broker-${REPO}-${DATE}-back\\"}"
                    JSON2="{\\"Snapshots\\":[{\\"Component\\":\\"main\\",\\"Name\\":\\"veil-broker-${REPO}-\${DATE}-back\\"}],\\"ForceOverwrite\\":true}"
                    curl -sS -X POST -H 'Content-Type: application/json' -d ${JSON1} http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/snapshots
                    curl -sS -X PUT -H 'Content-Type: application/json' -d ${JSON2} http://$APT_SRV:8008/api/publish/veil-broker-${REPO}/${DISTR}
                '''
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