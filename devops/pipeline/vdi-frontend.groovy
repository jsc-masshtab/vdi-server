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
        string(      name: 'BRANCH',               defaultValue: 'feature_tg_8124',              description: 'branch', trim: false),
        string(      name: 'REPO',                 defaultValue: 'vdi',              description: 'repo for uploading', trim: false),
        string(      name: 'VERSION',              defaultValue: '2.0.0',            description: 'base version',  trim: false),
        string(      name: 'AGENT',                defaultValue: 'debian9',          description: 'jenkins agent label for running the job', trim: false),
    ])
])

node("$AGENT") {

    env.PRJNAME="vdi-frontend"
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

                stage ('prepare environment') {
                    

                    sh script: '''
                        rm -rf ${WORKSPACE}/.git ${WORKSPACE}/.gitignore

                        echo "Install base packages"

                        sudo sed -i s/us\\./ru\\./g /etc/apt/sources.list
                        sudo apt-get update -y

                        sudo apt-get install -y postgresql-server-dev-9.6 python3-dev python3-setuptools python-dev gcc python3-pip postgresql htop mc nginx libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils

                        echo "Installing node v.10 && npm"
                        curl -sL https://deb.nodesource.com/setup_10.x | sudo bash
                        sudo apt-get install -y nodejs

                        # version software
                        VER="${VERSION}-${BUILD_NUMBER}"
                        sed -i "s:%%VER%%:$VER:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

                    '''
                }

                stage ('build') {
                    sh script: '''
                        cd ${WORKSPACE}/frontend
                        npm install --unsafe-perm
                        npm run build -- --prod

                        # frontend compiled ${WORKSPACE}/frontend/dist/frontend

                        mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"
                        sudo mkdir -p /opt/veil-vdi/www
                        cp -r ${WORKSPACE}/frontend/dist/frontend/* "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"
                        sudo cp -r ${WORKSPACE}/frontend/dist/frontend/* /opt/veil-vdi/www

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