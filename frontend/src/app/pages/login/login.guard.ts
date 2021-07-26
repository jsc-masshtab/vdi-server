import { Injectable } from '@angular/core';
import {
  CanActivate,
  CanActivateChild
} from '@angular/router';

import { AuthStorageService } from './authStorage.service';


@Injectable({
  providedIn: 'root',
})

export class LoginGuard implements CanActivate, CanActivateChild {
  constructor(private authStorageService: AuthStorageService) {}

  public canActivate(): boolean {
    return this.authStorageService.checkLogin();
  }

  public canActivateChild(): boolean {
    return this.authStorageService.checkLogin();
  }

}
