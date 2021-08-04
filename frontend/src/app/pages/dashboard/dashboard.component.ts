import { Component, OnInit, HostListener } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';

import { WebsocketService } from '../../shared/classes/websock.service';


@Component({
  selector: 'vdi-dashboard',
  templateUrl: './dashboard.component.html'

})
export class DashboardComponent implements OnInit {

  constructor(private ws: WebsocketService, public dialog: MatDialog) { }

  ngOnInit() {
    this.ws.init();
  }

  @HostListener('window:keydown', ['$event'])
  public closePopup(e) {
    if (e.keyCode === 27) {
      this.dialog.closeAll();
    }
  }
}
