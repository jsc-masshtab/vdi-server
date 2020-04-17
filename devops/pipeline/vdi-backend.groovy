def currentDate = new Date().format('yyyyMMddHHmmss')
def slackNotify = false

// git@192.168.10.145:vdi/vdiserver.git
// $BRANCH
// devops/pipeline/vdi-frontend.groovy

// build properties
properties([
    buildDiscarder(
        logRotator(
            artifactDaysToKeepStr: '',
            artifactNumToKeepStr: '',
            daysToKeepStr: '60',
            numToKeepStr: '30'
        )
    ),
    gitLabConnection('gitlab'),
    parameters([
        string(      name: 'BRANCH',               defaultValue: 'feature_tg_7701',              description: 'branch', trim: false),
        string(      name: 'REPO',                 defaultValue: 'vdi',              description: 'repo for uploading', trim: false),
        string(      name: 'VERSION',              defaultValue: '1.2.3',            description: 'base version',  trim: false),
        string(      name: 'AGENT',                defaultValue: 'debian9',          description: 'jenkins agent label for running the job', trim: false),
    ])
])

node("$AGENT") {

    env.PRJNAME="vdi-backend"
    env.NFS_DIR="vdi-deb"
    env.DEB_ROOT="${WORKSPACE}/devops/deb_config"
    env.DATE="$currentDate"


    notifyBuild(slackNotify, "STARTED", "Start new build. Version: ${DATE}")
    
    timestamps {
        ansiColor('xterm') {
            try {
                stage ('create environment') {
                    cleanWs()
                    def scmVars = checkout([ $class: 'GitSCM',
                        branches: [[name: '$BRANCH']],
                        doGenerateSubmoduleConfigurations: false,
                        extensions: [], submoduleCfg: [],
                        userRemoteConfigs: [[credentialsId: '', url: 'git@gitlab.bazalt.team:vdi/vdiserver.git']]
                    ])
                    
                    println "env.DATE - $env.DATE"
                }

                stage ('prepare build environment') {
                    

                    sh script: '''
                        rm -rf ${WORKSPACE}/.git ${WORKSPACE}/.gitignore

                        echo "Install base packages"

                        sudo sed -i s/us\\./ru\\./g /etc/apt/sources.list
                        sudo apt-get update -y

                        sudo apt-get install -y postgresql-server-dev-9.6 python3-dev python3-setuptools python-dev gcc python3-pip postgresql htop mc nginx libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils

                        echo "Installing additional packages"
                        sudo apt-get install -y supervisor logrotate
                        sudo apt-get install -y redis-server

                        # version software
                        VER="${VERSION}-${BUILD_NUMBER}"
                        sed -i "s:%%VER%%:$VER:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

                    '''
                }

                stage ('prepare virtual env') {
                    sh script: '''

                        export PYTHONPATH=${WORKSPACE}/backend
                        export PIPENV_PIPFILE=${WORKSPACE}/backend/Pipfile
                        # на версии 20.0.0 перестал работать pipenv
                        python3 -m pip install 'virtualenv<20.0.0' --force-reinstall
                        python3 -m pip install pipenv
                        pipenv install

                        #  копируем каталог с файлами фиртуального окружения в пакет
                        PIPENV_PATH=$(pipenv --venv)
                        mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env"
                        cp -r ${PIPENV_PATH}/* /opt/veil-vdi/env
                        cp -r ${PIPENV_PATH}/* "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env"
                    '''
                }

                stage ('prepare backend app') {
                    sh script: '''
                        mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
                        cp -r ${WORKSPACE}/backend/* /opt/veil-vdi/app
                        cp -r ${WORKSPACE}/backend/* "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
                    '''
                }

                stage ('prepare config') {
                    sh script: '''
                        # configure redis

                        sudo systemctl enable redis-server.service
                        sudo echo 'requirepass 4NZ7GpHn4IlshPhb' >> /etc/redis/redis.conf
                        sudo sed -i 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
                        sudo systemctl restart redis-server

                        # configure postgres

                        sudo cp ${WORKSPACE}/devops/deb_config/vdi-backend/root/opt/veil-vdi/other/vdi.postgresql /etc/postgresql/9.6/main/postgresql.conf
                        sudo sed -i 's/peer/trust/g' /etc/postgresql/9.6/main/pg_hba.conf
                        sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '192.168.20.112,127.0.0.1'/g" /etc/postgresql/9.6/main/postgresql.conf
                        echo 'host  vdi postgres  0.0.0.0/0  trust' | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
                        sudo systemctl restart postgresql

                        echo 'postgres:postgres' | sudo chpasswd
                        sudo su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
                        # На астре нету бездуховной кодировки en_US.UTF-8. Есть C.UTF-8
                        sudo su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;\" "

                        # setting up nginx

                        cp ${WORKSPACE}/devops/deb_config/vdi-backend/root/opt/veil-vdi/other/vdi.nginx /etc/nginx/conf.d/vdi_nginx.conf
                        rm /etc/nginx/sites-enabled/*
                        systemctl restart nginx

                        # apply database migrations

                        cd ${WORKSPACE}/backend
                        pipenv run alembic upgrade head

                        # creating logs directory at /var/log/veil-vdi/
                        mkdir -p /var/log/veil-vdi/

                        # deploying configuration files for logrotate
                        cp ${WORKSPACE}/devops/deb_config/vdi-backend/root/opt/veil-vdi/other/tornado.logrotate /etc/logrotate.d/veil-vdi

                        # deploying configuration files for supervisor
                        rm /etc/supervisor/supervisord.conf
                        cp ${WORKSPACE}/devops/deb_config/vdi-backend/root/opt/veil-vdi/other/supervisord.conf /etc/supervisor/supervisord.conf
                        supervisorctl reload

                        # vdi backend status
                        supervisorctl status

                    '''
                }

                stage ('build app') {
                    sh script: '''
                        make -C ${DEB_ROOT}/${PRJNAME}
                    '''
                }

                 stage ('publish to nfs') {
                    sh script: '''
                        # upload to nfs
                        mkdir -p /nfs/${NFS_DIR}
                        rm -f /nfs/vdi-deb/${PRJNAME}*.deb
                        cp ${DEB_ROOT}/${PRJNAME}/*.deb /nfs/${NFS_DIR}/
                    '''
                }
                
                stage ('publish to repo') {
                    sh script: '''
                        echo "REPO - $REPO"
                     
                        # upload files to temp repo
                        DEB=$(ls -1 ${DEB_ROOT}/${PRJNAME}/*.deb)
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
            } catch (InterruptedException err) {
                    currentBuild.result = 'FAILURE'
                    println "Build was interrupted manually"
                    println "Current build marked as ${currentBuild.result}: ${err.toString()}"
                    notifyBuild(slackNotify,"FAILED", "Build was interrupted manually. Version: ${DATE}")
                    throw err
            } catch (Exception err) {
                    currentBuild.result = 'FAILURE'
                    println "Something goes wrong"
                    println "Current build marked as ${currentBuild.result}: ${err.toString()}"
                    notifyBuild(slackNotify,"FAILED", "Something goes wrong. Version: ${DATE}")
                    throw err
            }
        }
    
    notifyBuild(slackNotify, "SUCCESSFUL","Build SUCCESSFUL. Version: ${DATE}")
    
    }
}

def notifyBuild(slackNotify, buildStatus, msg) {
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    def colorName = 'RED'
    def colorCode = '#FF0000'
    def subject = "${buildStatus}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'"
    def summary = "${subject} (${env.BUILD_URL})" + "\n"

    if (buildStatus == 'STARTED') {
        color = 'YELLOW'
        colorCode = '#FFFF00'
        summary += "${msg}"
    } else if (buildStatus == 'SUCCESSFUL') {
        color = 'GREEN'
        colorCode = '#00FF00'
        summary += "${msg}"
    } else {
        color = 'RED'
        colorCode = '#FF0000'
        summary += "${msg}"
    }
    if (slackNotify){
        slackSend (color: colorCode, message: summary)
    }
}