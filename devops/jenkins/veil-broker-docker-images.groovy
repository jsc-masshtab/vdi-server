library "vdi-server-libraries@$BRANCH"

def currentDate = new Date().format('yyyyMMddHHmmss')
def branch = buildParameters.branch()
def version = buildParameters.version()
def agents = buildParameters.agents()

notifyBuild("STARTED")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        DATE = "${currentDate}"
        NEXUS_DOCKER_REGISTRY = "nexus.bazalt.team"
        NEXUS_CREDS = credentials('nexus-jenkins-creds')
        DOCKER_IMAGE_NAME = "${NEXUS_DOCKER_REGISTRY}/veil-broker"
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
        string(      name: 'BRANCH',      defaultValue: branch,     description: 'branch')
        string(      name: 'VERSION',     defaultValue: version,    description: 'base version')
        choice(      name: 'AGENT',       choices: agents,          description: 'jenkins build agent')
        booleanParam(name: 'BACKEND',     defaultValue: true,       description: 'veil-broker-backend')
        booleanParam(name: 'FRONTEND',    defaultValue: true,       description: 'veil-broker-frontend')
    }

    stages {
        stage ('checkout') {
            steps {
                script {
                    buildSteps.gitCheckout("$BRANCH")
                }
            }
        }

        stage('build images') {
            parallel {
                stage ('backend. docker build') {
                    when {
                        beforeAgent true
                        expression { params.BACKEND == true }
                    }
                    environment {
                      COMPONENT = "backend"
                    }
                    steps {
                        script {
                            buildSteps.prepareBrokerImage()
                        }
                    }
                }

                stage ('frontend. docker build') {
                    when {
                        beforeAgent true
                        expression { params.FRONTEND == true }
                    }
                    environment {
                      COMPONENT = "frontend"
                    }
                    steps {
                        script {
                            buildSteps.prepareBrokerImage()
                        }
                    }
                }
            }
        }
    }
}