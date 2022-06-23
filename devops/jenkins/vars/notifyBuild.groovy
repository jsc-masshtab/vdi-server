def call(String buildStatus) {
    rocketNotify = true

    if (buildStatus == "STARTED") {
        status = ":bell: STARTED"
        msg = "Starting new build..."
    } else if (buildStatus == "FAILURE") {
        status = ":x: FAILED"
        msg = "Something goes wrong."
    } else if (buildStatus == "ABORTED") {
        status = ":heavy_multiplication_x: ABORTED"
        msg = "Build was interrupted manually."
    } else if (buildStatus == "SUCCESS") {
        status = ":white_check_mark: SUCCESS"
        msg = "Build SUCCESS."
    }

    println msg

    def summary = "${status}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})" + "\n"

    summary += "BRANCH: ${env.BRANCH} | REPO: ${env.REPO}"

    if (rocketNotify) {
        rocketSend (channel: 'jenkins-notify', message: summary, serverUrl: '192.168.14.210', trustSSL: true, rawMessage: true)
    }
}