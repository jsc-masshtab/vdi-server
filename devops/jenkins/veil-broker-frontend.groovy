def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        APT_SRV = "192.168.11.118"
        PRJNAME = "veil-broker-frontend"
        NFS_DIR = "/nfs/vdi-deb"
        DEB_ROOT = "${WORKSPACE}/devops/deb"
        DATE = "${currentDate}"
        VER = "${VERSION}-${BUILD_NUMBER}"
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
        string(      name: 'BRANCH',               defaultValue: 'dev',                   description: 'branch')
        string(      name: 'REPO',                 defaultValue: 'veil-broker-test',      description: 'repo for uploading')
        string(      name: 'VERSION',              defaultValue: '3.0.0',                 description: 'base version')
        string(      name: 'AGENT',                defaultValue: 'bld-agent',             description: 'jenkins build agent')
    }

    stages {
        stage ('checkout') {
            steps {
                cleanWs()
                checkout([ $class: 'GitSCM',
                    branches: [[name: '$BRANCH']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [], submoduleCfg: [],
                    userRemoteConfigs: [[credentialsId: '952e22ff-a42d-442c-83bd-76240a6ee793',
                    url: 'git@gitlab.bazalt.team:vdi/vdi-server.git']]
                ])
            }
        }

        stage('prepare build image') {
            steps {
                sh "docker build -f devops/docker/Dockerfile.vdi . -t vdi-builder:${VERSION}"
            }
        }

        stage ('build') {
            agent {
                docker {
                    image "vdi-builder:${VERSION}"
                    args '-u root:root -v /nfs:/nfs'
                    reuseNode true
                    label "${AGENT}"
                }
            }

            steps {
                sh script: '''
                    sed -i "s:%%VER%%:${VERSION}-${BUILD_NUMBER}:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

                    # clean npm cache
                    npm cache clean --force

                    cd ${WORKSPACE}/frontend
                    npm install --no-cache --unsafe-perm
                    npm run build -- --prod

                    # frontend compiled on ${WORKSPACE}/frontend/dist/frontend

                    mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"
                    cp -r ${WORKSPACE}/frontend/dist/frontend/* "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"

                    make -C ${DEB_ROOT}/${PRJNAME}

                    # upload to nfs
                    mkdir -p ${NFS_DIR}
                    rm -f ${NFS_DIR}/${PRJNAME}*.deb
                    cp ${DEB_ROOT}/${PRJNAME}/*.deb ${NFS_DIR}/
                '''
            }
        }

        stage ('publish to repo') {
            steps {
                sh script: '''
                    # remove old debs
                    curl -s "http://$APT_SRV:8008/api/repos/${REPO}/packages?q=${PRJNAME}" | jq -r '.[]' | while read KEY;
                    do
                        curl -X DELETE -H 'Content-Type: application/json' -d '{\"PackageRefs\":[\"'"$KEY"'\"]}' http://$APT_SRV:8008/api/repos/${REPO}/packages
                    done

                    # deploy new deb
                    DISTR=smolensk
                    DEB=$(ls -1 "${DEB_ROOT}/${PRJNAME}"/*.deb)
                    curl -sS -X POST -F file=@$DEB http://$APT_SRV:8008/api/files/${REPO}; echo ""
                    curl -sS -X POST http://$APT_SRV:8008/api/repos/${REPO}/file/${REPO}?forceReplace=1
                    JSON1="{\\"Name\\":\\"${REPO}-${DATE}\\"}"
                    JSON2="{\\"Snapshots\\":[{\\"Component\\":\\"main\\",\\"Name\\":\\"${REPO}-\${DATE}\\"}],\\"ForceOverwrite\\":true}"
                    curl -sS -X POST -H 'Content-Type: application/json' -d ${JSON1} http://$APT_SRV:8008/api/repos/${REPO}/snapshots
                    curl -sS -X PUT -H 'Content-Type: application/json' -d ${JSON2} http://$APT_SRV:8008/api/publish/${REPO}/${DISTR}
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