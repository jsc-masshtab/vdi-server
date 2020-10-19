def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        APT_SRV = "192.168.11.118"
        PRJNAME = "vdi-frontend"
        NFS_DIR = "/nfs/vdi-deb"
        DEB_ROOT = "${WORKSPACE}/devops/deb"
        DATE = "${currentDate}"
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
        string(      name: 'BRANCH',               defaultValue: 'dev',              description: 'branch')
        string(      name: 'REPO',                 defaultValue: 'vdi-testing',      description: 'repo for uploading')
        string(      name: 'VERSION',              defaultValue: '2.1.0',            description: 'base version')
        string(      name: 'AGENT',                defaultValue: 'debian9',          description: 'jenkins agent label for running the job')
    }

    stages {
        stage ('create environment') {
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

        stage ('prepare build environment') {
            environment {
                VER = "${VERSION}-${BUILD_NUMBER}"
            }

            steps {
                sh script: '''
                    rm -rf ${WORKSPACE}/.git ${WORKSPACE}/.gitignore
                    sed -i "s:%%VER%%:$VER:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"
                '''
            }
        }

        stage ('build') {
            steps {
                sh script: '''
                    # clean npm cache
                    npm cache clean --force

                    cd ${WORKSPACE}/frontend
                    npm install --no-cache --unsafe-perm
                    npm run build -- --prod

                    # frontend compiled on ${WORKSPACE}/frontend/dist/frontend

                    mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"
                    cp -r ${WORKSPACE}/frontend/dist/frontend/* "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"

                    make -C ${DEB_ROOT}/${PRJNAME}
                '''
            }
        }

        stage ('publish to nfs') {
            steps {
                sh script: '''
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
                    echo "Repo is - ${REPO}"
                        
                    #upload files
                    DEB=$(ls -1 "${DEB_ROOT}/${PRJNAME}"/*.deb)
                    for ITEM in $DEB
                    do
                        echo "Processing $ITEM packet:"
                        echo "$ITEM"
                        curl -sS -X POST -F file=@$ITEM http://$APT_SRV:8008/api/files/veil-${REPO}; echo ""
                    done

                    TIME=$(date +"%Y%m%d%H%M%S")
                    JSON1="{\\"Name\\":\\"veil-${REPO}-${TIME}\\"}"
                    echo ${JSON1}
                    JSON2="{\\"Snapshots\\":[{\\"Component\\":\\"main\\",\\"Name\\":\\"veil-${REPO}-\${TIME}\\"}]}"
                    echo ${JSON2}
                        
                    # upload folder
                    curl -sS -X POST http://$APT_SRV:8008/api/repos/veil-${REPO}/file/veil-${REPO}

                    # make snapshot repo
                    curl -sS -X POST -H 'Content-Type: application/json' -d ${JSON1} http://$APT_SRV:8008/api/repos/veil-${REPO}/snapshots

                    # switch publish repo - aptly publish switch veil test veil-test-20180906161745
                    curl -sS -X PUT -H 'Content-Type: application/json' -d ${JSON2} http://$APT_SRV:8008/api/publish/${REPO}/veil 
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