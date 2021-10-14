import { Component, OnInit } from '@angular/core';

import { WebsocketService } from '@app/core/services/websock.service';
import { AuthStorageService } from '@pages/login/authStorage.service';
import { LoginService } from '@pages/login/login.service';



@Component({
  selector: 'vdi-header-user',
  templateUrl: './header-user.component.html',
  styleUrls: ['./header-user.scss']
})
export class HeaderUserComponent implements OnInit {

  public user: string;
  public openMenu: boolean = false;

  constructor(private authStorageService: AuthStorageService, private loginService: LoginService, private ws: WebsocketService) {}

  ngOnInit() {
    this.user = this.authStorageService.getItemStorage('username');
  }

  public open(): void {
    this.openMenu = !this.openMenu;
  }

  public logout(): void {
    this.loginService.logout().subscribe(() => {
      this.authStorageService.logout();
      this.ws.close();
    });
  }

}
