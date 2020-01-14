import { WebsocketService } from './common/classes/websock.service';

import { Component, OnInit } from '@angular/core';


@Component({
  selector: 'vdi-dashboard',
  templateUrl: './dashboard.component.html'

})
export class DashboardComponent implements OnInit{

  constructor(private ws: WebsocketService) {}

  ngOnInit() {
    this.ws.init();
  }

}

