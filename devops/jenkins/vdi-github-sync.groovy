library "vdi-server-libraries@$BRANCH"

def currentDate = new Date().format('yyyyMMddHHmmss')
def branch = buildParameters.branch()
def agents = buildParameters.agents()

notifyBuild("STARTED")

pipeline {
    agent {
        label "${AGENT}"
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
        string(    name: 'BRANCH',     defaultValue: branch,     description: 'branch')
        choice(    name: 'AGENT',      choices: agents,          description: 'jenkins build agent')
    }

    stages {
        stage ('checkout') {
            steps {
                script {
                    buildSteps.gitCheckout("$BRANCH")
                }
            }
        }

        stage ('sync repos') {
            steps {
                sh script: """
                    bash devops/github/vdi-github-sync.sh
                """
            }
        }
    }
}