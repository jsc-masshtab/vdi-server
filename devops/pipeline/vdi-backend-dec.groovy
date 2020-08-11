def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

pipeline {
    agent {
        label "${AGENT}"
    }
    
    environment {
        PRJNAME = "vdi-backend"
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
        string(      name: 'VERSION',              defaultValue: '2.0.0',            description: 'base version')
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
                    sed -i "s:%%VER%%:${VER}:g" "${DEB_ROOT}/${PRJNAME}/root/DEBIAN/control"
                '''
            }
        }

        stage ('prepare backend app') {
            steps {
                sh script: '''
                    mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
                    rsync -a --delete ${WORKSPACE}/backend/ "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
                '''
            }
        }

        stage ('prepare virtual env') {
            steps {
                sh script: '''
                    # обновляем pip до последней версии
                    /usr/bin/python3 -m pip --no-cache-dir install -U pip
                    # устанавливаем virtualenv
                    /usr/bin/python3 -m pip --no-cache-dir install 'virtualenv==15.1.0' --force-reinstall
                    # создаем виртуальное окружение
                    sudo /usr/bin/python3 -m virtualenv ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env
                    # устанавливаем зависимости
                    cd ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app
                    sudo ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env/bin/python -m pip --no-cache-dir install -r requirements.txt
                '''
            }
        }

        stage ('build app') {
            steps {
                sh script: '''
                    cd backend/common
                    chmod +x compilemessages.sh
                    ./compilemessages.sh en
                    ./compilemessages.sh ru
                    cd ..
                    make -C "${DEB_ROOT}/${PRJNAME}"
                '''
            }
        }

        stage ('publish to nfs') {
            steps {
                sh script: '''
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
                    echo "REPO - ${REPO}"

                    # upload files to temp repo
                    DEB=$(ls -1 "${DEB_ROOT}/${PRJNAME}"/*.deb)
                    for ITEM in $DEB
                    do
                        echo "Processing packet: $ITEM"
                        curl -sS -X POST -F file=@$ITEM http://qa2:8008/api/files/veil-${REPO}
                        echo ""
                    done

                    # upload folder
                    curl -sS -X POST http://qa2:8008/api/repos/veil-${REPO}/file/veil-${REPO}
                    echo ""

                    # make snapshot repo
                    JSON1="{\\"Name\\":\\"veil-${REPO}-${DATE}\\"}"
                    echo "JSON1 - $JSON1"
                    curl -sS -X POST -H 'Content-Type: application/json' -d $JSON1 http://qa2:8008/api/repos/veil-${REPO}/snapshots
                    echo ""

                    # switch publish repo - aptly publish switch veil test veil-test-20180906161745
                    JSON2="{\\"Snapshots\\":[{\\"Component\\":\\"main\\",\\"Name\\":\\"veil-${REPO}-${DATE}\\"}]}"
                    echo "JSON2 - $JSON2"
                    curl -sS -X PUT -H 'Content-Type: application/json' -d $JSON2 http://qa2:8008/api/publish/${REPO}/veil
                    echo ""
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