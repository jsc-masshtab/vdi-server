def gitCheckout(String branchName) {
    cleanWs()
    checkout([ $class: 'GitSCM',
        branches: [[name: branchName]],
        doGenerateSubmoduleConfigurations: false,
        extensions: [], submoduleCfg: [],
        userRemoteConfigs: [[credentialsId: 'jenkins-vdi-token',
        url: 'http://gitlab.bazalt.team/vdi/vdi-server.git']]
    ])
}

def prepareBuildImage() {
    sh script: '''
        echo -n $NEXUS_CREDS_PSW | docker login -u $NEXUS_CREDS_USR --password-stdin $NEXUS_DOCKER_REGISTRY
        docker pull $DOCKER_IMAGE_NAME:latest || true
        cd devops/docker/builder
        docker build . --pull --cache-from $DOCKER_IMAGE_NAME:latest --tag $DOCKER_IMAGE_NAME:$VERSION
        docker push $DOCKER_IMAGE_NAME:$VERSION
        docker tag $DOCKER_IMAGE_NAME:$VERSION $DOCKER_IMAGE_NAME:latest
        docker push $DOCKER_IMAGE_NAME:latest
    '''
}

def deployToAptly() {
    sh script: '''
        APT_SRV="192.168.11.118"
        DISTR=1.7_x86-64

        # remove old debs
        curl -s "http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/packages?q=${PRJNAME}" | jq -r '.[]' | while read KEY;
        do
            curl -X DELETE -H 'Content-Type: application/json' -d '{\"PackageRefs\":[\"'"$KEY"'\"]}' http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/packages
        done

        # deploy new deb
        DEB=$(ls -1 "${DEB_ROOT}/${PRJNAME}"/*.deb)
        curl -sS -X POST -F file=@$DEB http://$APT_SRV:8008/api/files/veil-broker-${REPO}; echo ""
        curl -sS -X POST http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/file/veil-broker-${REPO}?forceReplace=1
        JSON1="{\\"Name\\":\\"veil-broker-${REPO}-${DATE}-back\\"}"
        JSON2="{\\"Snapshots\\":[{\\"Component\\":\\"main\\",\\"Name\\":\\"veil-broker-${REPO}-\${DATE}-back\\"}],\\"ForceOverwrite\\":true}"
        curl -sS -X POST -H 'Content-Type: application/json' -d ${JSON1} http://$APT_SRV:8008/api/repos/veil-broker-${REPO}/snapshots
        curl -sS -X PUT -H 'Content-Type: application/json' -d ${JSON2} http://$APT_SRV:8008/api/publish/veil-broker-${REPO}/${DISTR}
    '''
}

def prepareBrokerImage() {
    sh script: '''
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