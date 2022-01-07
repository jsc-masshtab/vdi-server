import { Component, OnInit, HostListener, OnDestroy } from '@angular/core';

import { MatDialog } from '@angular/material/dialog';
import { WebsocketService } from '@app/core/services/websock.service';
import { Observable } from 'rxjs';

import { ISettings, LoginService } from '../login/login.service';

@Component({
  selector: 'vdi-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  public settings$: Observable<ISettings>;
  constructor(private ws: WebsocketService, public dialog: MatDialog, private loginService: LoginService) { }

  ngOnInit() {
    this.ws.init();
    this.settings$ = this.loginService.getSettings();
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

