def rocketNotify = true

pipeline {
    agent {
        label "${AGENT}"
    }

    post {
        failure {
            println "Something goes wrong"
            println "Current build marked as ${currentBuild.result}"
            notifyBuild(rocketNotify,":x: FAILED")
        }

        aborted {
            println "Build was interrupted manually"
            println "Current build marked as ${currentBuild.result}"
            notifyBuild(rocketNotify,":x: FAILED")
        }

        success {
            notifyBuild(rocketNotify, ":white_check_mark: SUCCESSFUL")
        }
    }

    options {
        skipDefaultCheckout(true)
        buildDiscarder(logRotator(daysToKeepStr: '60', numToKeepStr: '100'))
        gitLabConnection('gitlab')
        timestamps()
        ansiColor('xterm')
    }

    parameters {
        string(      name: 'BRANCH',     defaultValue: 'dev',                                          description: 'branch')
        choice(      name: 'REPO',       choices: ['dev', 'prod-30', 'prod-31', 'prod-32', 'prod-40'], description: 'repo for uploading')
        string(      name: 'VERSION',    defaultValue: '4.0.0',                                        description: 'base version')
        string(      name: 'AGENT',      defaultValue: 'master',                                       description: 'jenkins build agent')
        booleanParam(name: 'BACKEND',    defaultValue: false,                                          description: 'veil-broker-backend')
        booleanParam(name: 'FRONTEND',   defaultValue: false,                                          description: 'veil-broker-frontend')
        booleanParam(name: 'DOCS',       defaultValue: false,                                          description: 'veil-broker-docs')
        booleanParam(name: 'THINCLIENT', defaultValue: false,                                          description: 'veil-connect-web')
        booleanParam(name: 'ISO',        defaultValue: false,                                          description: 'veil-broker-iso')
    }

    stages {
        stage ('create environment') {
            steps {
                notifyBuild(rocketNotify, ":bell: STARTED")
                cleanWs()
                git branch: '$BRANCH', url: 'git@gitlab.bazalt.team:vdi/vdi-server.git'
            }
        }

        stage ('build packages') {
            parallel {
                stage ('veil-broker-backend') {
                    when {
                        anyOf {
                            changeset "backend/**"
                            changeset "devops/deb/veil-broker-backend/**"
                            expression { params.BACKEND == true }
                        }
                    }
                    steps {
                        build job: 'vdi-backend', parameters: [string(name: 'BRANCH', value: "${BRANCH}"), string(name: 'REPO', value: "${REPO}"), string(name: 'VERSION', value: "${VERSION}")]
                    }
                }

                stage ('veil-broker-frontend') {
                    when {
                        anyOf {
                            changeset "frontend/**"
                            changeset "devops/deb/veil-broker-frontend/**"
                            expression { params.FRONTEND == true }
                        }
                    }
                    steps {
                        build job: 'vdi-frontend', parameters: [string(name: 'BRANCH', value: "${BRANCH}"), string(name: 'REPO', value: "${REPO}"), string(name: 'VERSION', value: "${VERSION}")]
                    }
                }

                stage ('veil-broker-docs') {
                    when {
                        anyOf {
                            changeset "docs/**"
                            changeset "devops/deb/veil-broker-docs/**"
                            expression { params.DOCS == true }
                        }
                    }
                    steps {
                        build job: 'vdi-docs', parameters: [string(name: 'BRANCH', value: "${BRANCH}"), string(name: 'REPO', value: "${REPO}"), string(name: 'VERSION', value: "${VERSION}")]
                    }
                }

                stage ('veil-connect-web') {
                    when {
                        anyOf {
                            changeset "frontend/projects/thin-client/**"
                            changeset "devops/deb/veil-connect-web/**"
                            expression { params.THINCLIENT == true }
                        }
                    }
                    steps {
                        build job: 'vdi-thin-client-web', parameters: [string(name: 'BRANCH', value: "${BRANCH}"), string(name: 'REPO', value: "${REPO}"), string(name: 'VERSION', value: "${VERSION}")]
                    }
                }
            }
        }

        stage ('veil-broker-iso') {
            when {
                expression { params.ISO == true }
            }
            steps {
                build job: 'vdi-broker-iso', parameters: [string(name: 'BRANCH', value: "${BRANCH}"), string(name: 'REPO', value: "${REPO}"), string(name: 'VERSION', value: "${VERSION}")]
            }
        }
    }
}

def notifyBuild(rocketNotify, buildStatus) {
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    def summary = "${buildStatus}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})" + "\n"

    summary += "BRANCH: ${BRANCH}. REPO: ${REPO}"

    if (rocketNotify){
        try {
            rocketSend (channel: 'jenkins-notify', message: summary, serverUrl: '192.168.14.210', trustSSL: true, rawMessage: true)
        } catch (Exception e) {
            println "Notify is failed"
        }
    }
}