import { WebsocketService } from '../../../common/classes/websock.service';
import { LoginService } from '../../../../login/login.service';
import { AuthStorageService } from '../../../../login/authStorage.service';
import { Component, OnInit } from '@angular/core';


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
