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
            numToKeepStr: '20'
        )
    ),
    gitLabConnection('gitlab'),
    parameters([
        string(      name: 'BRANCH',               defaultValue: 'feature_tg_7701',              description: 'branch', trim: false),
        string(      name: 'REPO',                 defaultValue: 'vdi',              description: 'repo for uploading', trim: false),
        booleanParam(name: 'DEB',                  defaultValue: true,               description: 'create DEB'),
        string(      name: 'VERSION',              defaultValue: '1.2.3',            description: 'base version',  trim: false),
        string(      name: 'AGENT',                defaultValue: 'debian9',          description: 'jenkins agent label for running the job', trim: false),
    ])
])

node("$AGENT") {

    env.APT_SRV="192.168.11.118"
    env.PRJNAME="vdi-frontend"
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
                    
                    env.GIT_COMMIT = scmVars.GIT_COMMIT
                    env.GIT_BRANCH = scmVars.GIT_BRANCH                    
                    env.GIT_COMMIT_DATE=sh(script:"git show -s --format=%ci", returnStdout: true).trim()

                    println "env.GIT_COMMIT - $env.GIT_COMMIT"
                    println "env.GIT_BRANCH - $env.GIT_BRANCH"
                    println "env.GIT_COMMIT_DATE - $env.GIT_COMMIT_DATE"

                    println "env.DATE - $env.DATE"
                }

                stage ('prepare environment') {
                    
                    VER = "${VERSION}-${BUILD_NUMBER}"

                    sh script: """
                        rm -rf ${WORKSPACE}/.git ${WORKSPACE}/.gitignore

                        echo "Install base packages"

                        sudo sed -i s/us\\./ru\\./g /etc/apt/sources.list
                        sudo apt-get update -y
                        sudo apt-get install -y postgresql-server-dev-9.6 python3-dev python3-setuptools python-dev gcc python3-pip postgresql htop mc nginx libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils

                        echo "Installing node v.10 && npm"
                        curl -sL https://deb.nodesource.com/setup_10.x | sudo bash
                        sudo apt-get install -y nodejs

                        echo "Version software: $VER"
                        
                        sed -i "s:%%VER%%:$VER:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

                    """
                }

                stage ('build') {
                    sh script: """
                        cd frontend
                        npm install --unsafe-perm
                        npm run build -- --prod

                        echo "frontend compiled frontend/dist/frontend"

                        mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi"
                        cp -r ./dist/frontend "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi"

                        [ "${DEB}" = "false" ] && return 0

                        make -C ${DEB_ROOT}/${PRJNAME}

                    """
                }

                stage ('publish to repo') {

                    JSON1 = "{\'Name\':\'veil-${REPO}-${DATE}\'}"
                    JSON2 = "{\'Snapshots\':[{\'Component\':\'main\',\'Name\':\'veil-${REPO}-${DATE}\'}]}"

                    sh script: """
                        echo "Repo is - $REPO"

                        # upload to nfs
                        mkdir -p /nfs/vdi-deb
                        rm -f /nfs/vdi-deb/vdi-frontend*.deb
                        cp $DEB_ROOT/$PRJNAME/*.deb /nfs/vdi-deb/
                        
                        # upload files to temp repo
                        DEB=\$(ls -1 $DEB_ROOT/$PRJNAME/*.deb)
                        echo "\$DEB"

                        for ITEM in \$DEB
                        do
                            echo "Processing \$ITEM packet:"
                            echo "\$ITEM"
                            curl -sS -X POST -F file=@\$ITEM http://$APT_SRV:8008/api/files/veil-$REPO; echo ""
                        done

                        # upload folder
                        curl -sS -X POST http://$APT_SRV:8008/api/repos/veil-$REPO/file/veil-$REPO; echo ""

                        # make snapshot repo
                        echo $JSON1
                        curl -sS -X POST -H 'Content-Type: application/json' -d $JSON1 http://$APT_SRV:8008/api/repos/veil-$REPO/snapshots; echo ""

                        # switch publish repo - aptly publish switch veil test veil-test-20180906161745
                        echo $JSON2
                        curl -sS -X PUT -H 'Content-Type: application/json' -d $JSON2 http://$APT_SRV:8008/api/publish/$REPO/veil; echo ""
                    """
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