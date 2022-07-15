import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  CanActivateChild
} from '@angular/router';

import { AuthStorageService } from './authStorage.service';
import { environment } from 'environments/environment';

@Injectable({
  providedIn: 'root',
})

export class LoginGuard implements CanActivate, CanActivateChild {

  constructor(
    private authStorageService: AuthStorageService
  ) {}

  public canActivate(): boolean {
    return this.authStorageService.checkLogin();
  }

  public canActivateChild(route: ActivatedRouteSnapshot): boolean {
    const path = route.routeConfig.path;

    if (path === 'settings/services' && environment.multiple) {
      return false;
    }

    if (path === 'statistics/statistics-web' && environment.multiple) {
      return false;
    }

    return this.authStorageService.checkLogin();
  }
}
