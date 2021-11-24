def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

def notifyBuild(rocketNotify, buildStatus, msg) {
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    def summary = "${buildStatus}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})" + "\n"

    summary += "${msg}"

    if (rocketNotify){
        rocketSend (channel: 'jenkins-notify', message: summary, serverUrl: '192.168.14.210', trustSSL: true, rawMessage: true)
    }
}


notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        DATE = "${currentDate}"
        APT_SRV = "192.168.11.118"
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
        string(      name: 'AGENT',       defaultValue: 'bld-agent',               description: 'jenkins build agent')
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

        stage ('sync repos') {

            steps {
                sh script: '''
                    bash devops/github/vdi-github-sync.sh
                '''
            }
        }
    }
}

