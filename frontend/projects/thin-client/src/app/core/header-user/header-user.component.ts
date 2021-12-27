import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';

import { GenerateQrcodeComponent } from '../../components/generate-qrcode/generate-qrcode.component';
import { AuthStorageService } from '../services/authStorage.service';
import { LoginService } from '../services/login.service';






@Component({
  selector: 'tc-header-user',
  templateUrl: './header-user.component.html',
  styleUrls: ['./header-user.scss']
})
export class HeaderUserComponent implements OnInit {

  public user: string;
  public openMenu: boolean = false;

  constructor(private authStorageService: AuthStorageService, private loginService: LoginService, public dialog: MatDialog) {}

  ngOnInit() {
    this.user = this.authStorageService.getItemStorage('username');
  }

  public open(): void {
    this.openMenu = !this.openMenu;
  }

  public logout(): void {
    this.loginService.logout().subscribe(() => {
      this.authStorageService.logout();
    });
  }

  public openGenerateQrcode() {
    this.dialog.open(GenerateQrcodeComponent, {
      disableClose: true,
      width: '500px'
    });
  }
}
