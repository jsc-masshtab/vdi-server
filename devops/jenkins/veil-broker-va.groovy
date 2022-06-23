library "vdi-server-libraries@$BRANCH"

def currentDate = new Date().format('yyyyMMddHHmmss')
def branch = buildParameters.branch()
def repos = buildParameters.repos()
def version = buildParameters.version()
def agents = buildParameters.agents()

notifyBuild("STARTED")

pipeline {
    agent {
        label "${AGENT}"
    }

    environment {
        DATE = "${currentDate}"
        VEIL_ADDRESS = "192.168.11.102"
        VEIL_NODE_ID = "de4a8586-db6d-480f-bc60-f5868e229191"
        VEIL_DATAPOOL_ID = "5335a616-073a-4d6e-b00c-9612a2eb08d3"
        ASTRA_TEMPLATE_ID = "f76da49a-01d4-4749-91d1-084c06b8b23c"
        VM_NAME = "veil-broker-va-${VERSION}"
        VM_USERNAME = "astravdi"
        TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VyX2lkIjo0LCJ1c2VybmFtZSI6ImFwaSIsImV4cCI6MTk2MTM5MzM1OCwic3NvIjpmYWxzZSwib3JpZ19pYXQiOjE2NDY4OTczNTh9.D6cxPDlPneURRLrKTpfsv_MTTvGxoDp9rJH-kokaweUr3eMarCZ7ZG0IpOaO5i5KBuf0q1es8q9HEpa8zhpZVOb2joNtTD5im9-NQO4ffZf_ZucQDzv7sZfTPTrMFBZA3WsEruAYSs1bI7yiemf5SvTurYYdyxNgWZBvXfbXpNeXT6YuNiwFKCDe69Cg65_2bee398vGW3lrNZajdiliJPawq9Q-OqqHnrkdwwyv4CzA9FQEs2FabwEqqZpyJyVni1DF9wS8U1MXsCKVoCOagZBvwrxvz5yeTMPKL_ozgbrWN_mSmmPMnBQGXCdGHSiagBU9f2MhY7Hpu-8SzXRSof7Qj-eHp03jDgAbfknuNtFMazHtE5hppQjQlkLEA0Di-7Mtq1Q1XDKRQ6d0LaAwbk098irPOfSU2GjdaHYfT0NA_PwBzDC-Ke8eQnFDygH6K3ezVfTgYgkRUZghpl-aLuN7SEYInJLM12jWTvh5IFcfDInpgasQDdaEjOH2li1rixpWWkTJu-xD-PNSysT2pSdlTLsqshmJL2B1ixrQVCcGemI3TqNj61CnMBi1aELzTycWWW6OuYAAvZXQ4K92npJr1YRHxAR6dLjQPJmHZr0J31Bph2bWUPYAV1Zp1kpkliRrY1vQJKxwqEg9hPxc3Q-z70gPCdQsGeQMkQqo3VI"
        NEXUS_DOCKER_REGISTRY = "nexus.bazalt.team"
        DOCKER_IMAGE_NAME = "${NEXUS_DOCKER_REGISTRY}/dwdraju/alpine-curl-jq"
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
        choice(    name: 'REPO',       choices: repos,           description: 'repo for uploading')
        string(    name: 'VERSION',    defaultValue: version,    description: 'base version')
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

        stage('prepare build image') {
            steps {
                sh 'docker pull $DOCKER_IMAGE_NAME:latest'
            }
        }

        stage ('Create vm from template') {
            agent {
                docker {
                    image "${DOCKER_IMAGE_NAME}"
                    args '-u root:root -v /nfs:/nfs'
                    reuseNode true
                    label "${AGENT}"
                }
            }

            steps {
                sh script: '''
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

                      if [ "$TASK_STATUS" == "null" ]; then exit 1; fi
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

                    sleep 180

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