library "vdi-server-libraries@$BRANCH"

def branch = buildParameters.branch()
def repos = buildParameters.repos()
def version = buildParameters.version()

notifyBuild("STARTED")

pipeline {
    agent {
        label "master"
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
    }

    parameters {
        string(      name: 'BRANCH',        defaultValue: branch,     description: 'branch')
        choice(      name: 'REPO',          choices: repos,           description: 'repo for uploading')
        string(      name: 'VERSION',       defaultValue: version,    description: 'base version')
        booleanParam(name: 'BACKEND',       defaultValue: false,      description: 'veil-broker-backend')
        booleanParam(name: 'FRONTEND',      defaultValue: false,      description: 'veil-broker-frontend')
        booleanParam(name: 'DOCS',          defaultValue: false,      description: 'veil-broker-docs')
        booleanParam(name: 'THINCLIENT',    defaultValue: false,      description: 'veil-connect-web')
        booleanParam(name: 'DOCKER',        defaultValue: false,      description: 'veil-broker docker images')
        booleanParam(name: 'ISO',           defaultValue: false,      description: 'veil-broker-iso')
    }

    stages {
        stage ('create environment') {
            steps {
                script {
                    buildSteps.gitCheckout("$BRANCH")
                }
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

                stage ('veil-broker-docker-images') {
                    when {
                        anyOf {
                            changeset "backend/**"
                            changeset "frontend/**"
                            changeset "docs/**"
                            changeset "devops/docker/prod/**"
                            expression { params.DOCKER == true }
                        }
                    }
                    steps {
                        build job: 'veil-broker-docker-images', parameters: [string(name: 'BRANCH', value: "${BRANCH}"), string(name: 'VERSION', value: "${VERSION}")]
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