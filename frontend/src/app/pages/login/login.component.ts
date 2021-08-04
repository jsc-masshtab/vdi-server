import {
  trigger,
  style,
  transition,
  animate
} from '@angular/animations';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';

import { ErrorsService } from '../../core/components/errors/errors.service';
import { AuthStorageService } from './authStorage.service';
import { LoginService } from './login.service';

@Component({
  selector: 'vdi-login',
  templateUrl: './login.html',
  styleUrls: ['./login.scss'],
  animations: [
    trigger('animForm', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('150ms', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        style({ opacity: 1 }),
        animate('150ms', style({ opacity: 0 }))
      ])
    ])
  ]
})

export class LoginComponent implements OnInit {

  public loaded: boolean = false;
  public loginForm: FormGroup;

  public useCode = new FormControl(false)

  constructor(private fb: FormBuilder,
              private authStorageService: AuthStorageService,
              private loginService: LoginService,
              private route: Router,
              private errorService: ErrorsService) { this.routePage(); }

  ngOnInit() {
    this.loaded = true;
  }

  private createForm(): void {
    if (!this.loginForm) {
      this.loginForm = this.fb.group({
        username: '' ,
        password: '',
        code: '',
        ldap: false
      });
    } else {
      return;
    }
  }

  private routePage(): void {
    if (this.authStorageService.checkLogin()) {
      this.route.navigate(['/pages']);
    } else {
      this.createForm();
    }
  }

  public send() {
    this.loginService.auth(this.loginForm.value).subscribe((res: { data: { access_token: string, expires_on: string, username: string }} & { errors: [] } ) => {
      if (res && res.data) {
        this.authStorageService.saveInStorage(res.data);
        this.routePage();
      }

      if (res.errors !== undefined) {
        this.errorService.setError(res.errors);
      }
    });
  }
}