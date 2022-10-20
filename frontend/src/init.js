(() => {
  const xmlHttpRequest = new XMLHttpRequest();
  const broker_name = localStorage.getItem('broker_name');
  const preloader = document.getElementById('preloader-title');

  document.title = broker_name || '';
  preloader.innerText = broker_name;

  xmlHttpRequest.onreadystatechange = function () {
    if (xmlHttpRequest.readyState == XMLHttpRequest.DONE) {

      const response = JSON.parse(xmlHttpRequest.response);
      const data = response.data;
      
      preloader.innerText = data.broker_name;
      document.title = data.broker_name || '';

      localStorage.setItem('broker_name', data.broker_name);
    }
  };

  xmlHttpRequest.open('GET', `/api/settings/`);
  xmlHttpRequest.send();
})();
