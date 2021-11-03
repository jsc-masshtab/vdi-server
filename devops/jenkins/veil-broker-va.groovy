def currentDate = new Date().format('yyyyMMddHHmmss')
def rocketNotify = true

notifyBuild(rocketNotify, ":bell: STARTED", "Start new build. Version: ${currentDate}")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        APT_SRV = "192.168.11.118"
        DATE = "${currentDate}"
        VEIL_ADDRESS = "192.168.11.102"
        VEIL_USER = "api"
        VEIL_PASS = "Passw0rd!"
        VEIL_NODE_ID = "4c2d5d96-966e-4ca5-aee8-d9f6e226c053"
        VEIL_DATAPOOL_ID = "9868f5b7-2616-4fa3-ba54-ced42e3e5ab7"
        ASTRA_TEMPLATE_ID = "b31ee8d8-c60f-4c4b-a96b-58bd5fec2d16"
        VM_NAME = "veil-broker-va-${VERSION}"
        VM_USERNAME = "user"
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
        string(      name: 'BRANCH',      defaultValue: 'dev',                     description: 'branch')
        choice(      name: 'REPO',        choices: ['test', 'prod-30', 'prod-31'], description: 'repo for uploading')
        string(      name: 'VERSION',     defaultValue: '3.1.1',                   description: 'base version')
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

        stage ('Create vm from template') {
            agent {
                docker {
                    image "dwdraju/alpine-curl-jq"
                    args '-u root:root -v /nfs:/nfs'
                    reuseNode true
                    label "${AGENT}"
                }
            }

            steps {
                sh script: '''
                    # Auth
                    TOKEN=$(curl -s -f -S -H "Content-Type: application/json" \
                    -d "{\\"username\\":\\"${VEIL_USER}\\", \\"password\\":\\"${VEIL_PASS}\\"}" \
                    http://${VEIL_ADDRESS}/auth/ | jq -r .token)

                    # Clone VM from template
                    TASK_ID=$(curl -s -f -S -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    -d "{\\"node\\":\\"${VEIL_NODE_ID}\\", \\"verbose_name\\":\\"${VM_NAME}\\", \\"datapool\\":\\"${VEIL_DATAPOOL_ID}\\"}" \
                    http://${VEIL_ADDRESS}/api/domains/${ASTRA_TEMPLATE_ID}/clone/?async=1 | jq -r ._task.id)

                    # Waiting for VM creation
                    until [ "$TASK_STATUS" == "SUCCESS" ]
                    do
                      sleep 10
                      TASK_STATUS=$(curl -s -f -S -H "Content-Type: application/json" \
                      -H "Authorization: jwt ${TOKEN}" \
                      http://${VEIL_ADDRESS}/api/tasks/${TASK_ID}/ | jq -r .status)
                      TASK_PROGRESS=$(curl -s -f -S -H "Content-Type: application/json" \
                      -H "Authorization: jwt ${TOKEN}" \
                      http://${VEIL_ADDRESS}/api/tasks/${TASK_ID}/ | jq -r .progress)

                      echo "Task status is: $TASK_STATUS, progress: $TASK_PROGRESS %"
                    done

                    # Get new VM id
                    VM_ID=$(curl -s -f -S -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    http://${VEIL_ADDRESS}/api/domains/?name=${VM_NAME} | jq -r .results[].id)

                    # Convert template to VM
                    curl -s -f -S -XPUT -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    -d "{\\"template\\":\\"false\\"}" \
                    http://${VEIL_ADDRESS}/api/domains/${VM_ID}/template/

                    # Create ssh keys
                    apk update && apk add --no-cache openssh-keygen openssh-client
                    ssh-keygen -t rsa -q -f "$HOME/.ssh/id_rsa" -N ""
                    PUBLIC_KEY=$(cat $HOME/.ssh/id_rsa.pub)

                    # Add authorized key
                    curl -s -f -S -XPOST -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    -d "{\\"create_user\\":false, \\"ssh_user\\":\\"${VM_USERNAME}\\", \\"ssh_key\\":\\"${PUBLIC_KEY}\\"}" \
                    http://${VEIL_ADDRESS}/api/domains/${VM_ID}/ssh-inject/

                    # Start VM
                    curl -s -f -S -XPOST -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    http://${VEIL_ADDRESS}/api/domains/${VM_ID}/start/

                    sleep 120

                    # Get VM ip address
                    VM_IP=$(curl -s -f -S -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    http://${VEIL_ADDRESS}/api/domains/?name=${VM_NAME} | jq -r .results[].guest_utils.ipv4[0])

                    # Install broker
                    ssh -o StrictHostKeyChecking=no $VM_USERNAME@$VM_IP '
                      rm -f *.iso
                      wget -nv -r -nd --no-parent -A 'veil-broker-${REPO}-${VERSION}-*.iso' http://192.168.10.144/veil-broker-iso/${REPO}/
                      sudo mount -o loop "$(ls -1 *.iso)" /media/cdrom
                      sudo bash /media/cdrom/install.sh
                      rm -f *.iso
                    '

                    # Stop VM
                    curl -s -f -S -XPOST -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    -d "{\\"force\\":false}" \
                    http://${VEIL_ADDRESS}/api/domains/$VM_ID/shutdown/

                    sleep 60

                    # Backup VM
                    TASK_ID=$(curl -s -f -S -XPOST -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    -d "{\\"domain\\":\\"$VM_ID\\", \\"datapool\\":\\"${VEIL_DATAPOOL_ID}\\", \\"compress\\":true, \\"limit_days\\":1}" \
                    http://${VEIL_ADDRESS}/api/domains/backup/?async=1 | jq -r ._task.id)

                    # Waiting for VM backup creation
                    unset TASK_STATUS
                    until [ "$TASK_STATUS" == "SUCCESS" ]
                    do
                      sleep 10
                      TASK_STATUS=$(curl -s -f -S -H "Content-Type: application/json" \
                      -H "Authorization: jwt ${TOKEN}" \
                      http://${VEIL_ADDRESS}/api/tasks/${TASK_ID}/ | jq -r .status)
                      TASK_PROGRESS=$(curl -s -f -S -H "Content-Type: application/json" \
                      -H "Authorization: jwt ${TOKEN}" \
                      http://${VEIL_ADDRESS}/api/tasks/${TASK_ID}/ | jq -r .progress)

                      echo "Task status is: $TASK_STATUS, progress: $TASK_PROGRESS %"
                    done

                    # Remove VM
                    curl -s -f -S -H "Content-Type: application/json" \
                    -H "Authorization: jwt ${TOKEN}" \
                    -d "{\\"full\\":\\"true\\"}" \
                    http://${VEIL_ADDRESS}/api/domains/${VM_ID}/remove/
                '''
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