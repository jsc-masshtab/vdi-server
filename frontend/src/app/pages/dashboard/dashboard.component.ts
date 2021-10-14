import { Component, OnInit, HostListener, OnDestroy } from '@angular/core';

import { MatDialog } from '@angular/material/dialog';
import { WebsocketService } from '@app/core/services/websock.service';


@Component({
  selector: 'vdi-dashboard',
  templateUrl: './dashboard.component.html'

})
export class DashboardComponent implements OnInit, OnDestroy {

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

  ngOnDestroy() {
    this.dialog.closeAll();
  }
}

