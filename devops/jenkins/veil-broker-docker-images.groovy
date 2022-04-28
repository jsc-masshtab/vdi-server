def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        DATE = "${currentDate}"
        VER = "${VERSION}-${BUILD_NUMBER}"
        NEXUS_DOCKER_REGISTRY = "nexus.bazalt.team"
        NEXUS_CREDS = credentials('nexus-jenkins-creds')
        DOCKER_IMAGE_NAME = "${NEXUS_DOCKER_REGISTRY}/veil-broker"
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
        string(      name: 'BRANCH',   defaultValue: 'dev',                       description: 'branch')
        string(      name: 'VERSION',  defaultValue: '4.0.0',                     description: 'base version')
        choice(      name: 'AGENT',    choices: ['cloud-ubuntu-20', 'bld-agent'], description: 'jenkins build agent')
        booleanParam(name: 'BACKEND',  defaultValue: true,                        description: 'veil-broker-backend')
        booleanParam(name: 'FRONTEND', defaultValue: true,                        description: 'veil-broker-frontend')
        booleanParam(name: 'NGINX',    defaultValue: false,                       description: 'veil-broker-nginx')
    }

    stages {
        stage ('checkout') {
            steps {
                cleanWs()
                checkout([ $class: 'GitSCM',
                    branches: [[name: '$BRANCH']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [], submoduleCfg: [],
                    userRemoteConfigs: [[credentialsId: 'jenkins-vdi-token',
                    url: 'http://gitlab.bazalt.team/vdi/vdi-server.git']]
                ])
            }
        }

        stage('build images') {
            parallel {
                stage ('backend. docker build') {
                    when {
                        beforeAgent true
                        expression { params.BACKEND == true }
                    }
                    steps {
                        sh script: '''
                            COMPONENT="backend"
                            echo -n $NEXUS_CREDS_PSW | docker login -u $NEXUS_CREDS_USR --password-stdin $NEXUS_DOCKER_REGISTRY
                            docker pull $DOCKER_IMAGE_NAME-$COMPONENT:latest || true
                            docker build . --pull \
                                           --cache-from $DOCKER_IMAGE_NAME-$COMPONENT:latest \
                                           -f devops/docker/prod/Dockerfile.$COMPONENT \
                                           --tag $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION
                            docker push $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION
                            docker tag $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION $DOCKER_IMAGE_NAME-$COMPONENT:latest
                            docker push $DOCKER_IMAGE_NAME-$COMPONENT:latest
                        '''
                    }
                }

                stage ('frontend. docker build') {
                    when {
                        beforeAgent true
                        expression { params.FRONTEND == true }
                    }
                    steps {
                        sh script: '''
                            COMPONENT="frontend"
                            echo -n $NEXUS_CREDS_PSW | docker login -u $NEXUS_CREDS_USR --password-stdin $NEXUS_DOCKER_REGISTRY
                            docker pull $DOCKER_IMAGE_NAME-$COMPONENT:latest || true
                            docker build . --pull \
                                           --cache-from $DOCKER_IMAGE_NAME-$COMPONENT:latest \
                                           -f devops/docker/prod/Dockerfile.$COMPONENT \
                                           --tag $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION
                            docker push $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION
                            docker tag $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION $DOCKER_IMAGE_NAME-$COMPONENT:latest
                            docker push $DOCKER_IMAGE_NAME-$COMPONENT:latest
                        '''
                    }
                }

                stage ('nginx. docker build') {
                    when {
                        beforeAgent true
                        expression { params.NGINX == true }
                    }
                    steps {
                        sh script: '''
                            COMPONENT="nginx"
                            echo -n $NEXUS_CREDS_PSW | docker login -u $NEXUS_CREDS_USR --password-stdin $NEXUS_DOCKER_REGISTRY
                            docker pull $DOCKER_IMAGE_NAME-$COMPONENT:latest || true
                            docker build . --pull \
                                           --cache-from $DOCKER_IMAGE_NAME-$COMPONENT:latest \
                                           -f devops/docker/prod/Dockerfile.$COMPONENT \
                                           --tag $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION
                            docker push $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION
                            docker tag $DOCKER_IMAGE_NAME-$COMPONENT:$VERSION $DOCKER_IMAGE_NAME-$COMPONENT:latest
                            docker push $DOCKER_IMAGE_NAME-$COMPONENT:latest
                        '''
                    }
                }
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