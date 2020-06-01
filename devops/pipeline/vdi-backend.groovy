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
            numToKeepStr: '100'
        )
    ),
    gitLabConnection('gitlab'),
    parameters([
        string(      name: 'BRANCH',               defaultValue: 'dev',           description: 'branch', trim: false),
        // string(      name: 'REPO',                 defaultValue: 'vdi',              description: 'repo for uploading', trim: false),
        string(      name: 'REPO',                 defaultValue: 'vdi-testing',      description: 'repo for uploading', trim: false),
        string(      name: 'VERSION',              defaultValue: '2.0.0',            description: 'base version',  trim: false),
        string(      name: 'AGENT',                defaultValue: 'debian9',          description: 'jenkins agent label for running the job', trim: false),
    ])
])

node("$AGENT") {

    env.PRJNAME="vdi-backend"
    env.NFS_DIR="vdi-deb"
    env.DEB_ROOT="${WORKSPACE}/devops/deb"
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

                stage ('prepare backend app') {
                    sh script: '''
                        sudo rm -rf /opt/veil-vdi/app
                        sudo rm -rf /opt/veil-vdi/other

                        sudo mkdir -p /opt/veil-vdi/app
                        sudo mkdir -p /opt/veil-vdi/other

                        sudo rsync -a --delete ${WORKSPACE}/backend/ /opt/veil-vdi/app
                        sudo rsync -a --delete "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/" /opt/veil-vdi/other

                        mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
                        rsync -a --delete ${WORKSPACE}/backend/ "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"

                    '''
                }

                stage ('prepare virtual env') {
                    sh script: '''

                        # обновляем pip до последней версии
                        /usr/bin/python3 -m pip install -U pip
                        # устанавливаем virtualenv
                        /usr/bin/python3 -m pip install 'virtualenv==15.1.0' --force-reinstall
                        # создаем виртуальное окружение
                        sudo rm -rf /opt/veil-vdi/env
                        sudo /usr/bin/python3 -m virtualenv /opt/veil-vdi/env
                        # устанавливаем зависимости
                        cd /opt/veil-vdi/app
                        sudo /opt/veil-vdi/env/bin/python -m pip install -r requirements.txt

                        # копируем каталог с файлами виртуального окружения в пакет
                        mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env"
                        rsync -a --delete /opt/veil-vdi/env/ "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env"

                    '''
                }

                stage ('configure application') {
                    sh script: '''

                        # генерируем local_settings только если его не существует
                        if [ ! -f /opt/veil-vdi/app/local_settings.py ]; then
                            cd /opt/veil-vdi/app
                            sudo /opt/veil-vdi/env/bin/python /opt/veil-vdi/app/create_local_settings.py
                        fi

                        # configure redis

                        # берем из файла ключи доступа
                        REDIS_PASS="$(grep -r 'REDIS_PASSWORD' /opt/veil-vdi/app/local_settings.py | sed -r "s/REDIS_PASSWORD = '(.+)'/\\1/g")"

                        sudo systemctl enable redis-server.service

                        sudo cp "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/vdi.redis" /etc/redis/redis.conf
                        # устанавливаем пароль для подключения
                        echo "requirepass ${REDIS_PASS}" | sudo tee -a /etc/redis/redis.conf

                        sudo systemctl restart redis-server

                        # configure postgres

                        # перекладываем наш из conf
                        sudo cp "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/vdi.postgresql" /etc/postgresql/9.6/main/postgresql.conf
 
                        #fix locale
                        sudo localedef -i en_US -f UTF-8 en_US.UTF-8
                        
                        sudo systemctl restart postgresql

                        # cоздаем БД

                        # берем из файла ключи доступа
                        DB_PASS="$(grep -r 'DB_PASS' /opt/veil-vdi/app/local_settings.py | sed -r "s/DB_PASS = '(.+)'/\\1/g")"

                        echo 'postgres:postgres' | sudo chpasswd
                        sudo -u postgres -i psql -c "ALTER ROLE postgres PASSWORD '${DB_PASS}';"

                        # На астре нету бездуховной кодировки en_US.UTF-8. Есть C.UTF-8
                        sudo -u postgres -i psql -c "create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;" || true

                        # apply database migrations

                        export PYTHONPATH=/opt/veil-vdi/app
                        cd /opt/veil-vdi/app
                        /opt/veil-vdi/env/bin/python /opt/veil-vdi/env/bin/alembic upgrade head

                        # setting up nginx

                        cp "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/veil_ssl/veil_default.crt" /opt/veil-vdi/other/veil_ssl/veil_default.crt
                        cp "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/veil_ssl/veil_default.key" /opt/veil-vdi/other/veil_ssl/veil_default.key
                        sudo cp "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/vdi.nginx" /etc/nginx/conf.d/vdi_nginx.conf
                        sudo rm /etc/nginx/sites-enabled/* || true

                        sudo systemctl restart nginx

                    '''
                }


                stage ('additional settings') {
                    sh script: '''
                        # creating logs directory at /var/log/veil-vdi/
                        sudo mkdir -p /var/log/veil-vdi/

                        # deploying configuration files for logrotate
                        sudo cp "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/tornado.logrotate" /etc/logrotate.d/veil-vdi

                        # deploying configuration files for supervisor
                        sudo rm /etc/supervisor/supervisord.conf
                        sudo cp "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/other/supervisord.conf" /etc/supervisor/supervisord.conf

                        sudo chown jenkins: -R /opt/veil-vdi/

                        sudo supervisorctl reload

                        # vdi backend status
                        sudo supervisorctl status || true
                    '''
                }
                
                stage ('build app') {
                    sh script: '''
                        make -C "${DEB_ROOT}/${PRJNAME}"
                    '''
                }

                 stage ('publish to nfs') {
                    sh script: '''
                        # upload to nfs
                        mkdir -p /nfs/${NFS_DIR}
                        rm -f /nfs/vdi-deb/${PRJNAME}*.deb
                        cp "${DEB_ROOT}/${PRJNAME}"/*.deb /nfs/${NFS_DIR}/
                    '''
                }
                
                stage ('publish to repo') {
                    sh script: '''
                        echo "REPO - $REPO"
                     
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