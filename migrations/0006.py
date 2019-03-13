


async def run():
    await AddNode('192.168.20.121')
    path = await DownloadImage()
    await UploadImage(path)