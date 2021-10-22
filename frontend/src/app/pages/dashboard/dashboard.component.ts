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
    
    if (e.key === 'Escape') {
      this.dialog.closeAll();
    }

    if (e.key === 'Enter' && this.dialog.openDialogs.length) {
      if (this.dialog.openDialogs[this.dialog.openDialogs.length - 1].componentInstance.send) {
        this.dialog.openDialogs[this.dialog.openDialogs.length - 1].componentInstance.send();
      }
    }
  }

  ngOnDestroy() {
    this.dialog.closeAll();
  }
}

