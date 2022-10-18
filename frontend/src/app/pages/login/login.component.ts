import {
  trigger,
  style,
  transition,
  animate
} from '@angular/animations';

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';

import { ErrorsService } from '../../core/components/errors/errors.service';
import { AuthStorageService } from './authStorage.service';
import { ISettings, LoginService } from './login.service';

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
  public settings$: Observable<ISettings>;
  public useCode = new FormControl(false)
  public ldap = '';
  public broker_name = '';
  
  info$ = this.loginService.getCopyrightInfo();

  constructor(private fb: FormBuilder,
              private authStorageService: AuthStorageService,
              private loginService: LoginService,
              private route: Router,
              private errorService: ErrorsService) { this.routePage(); }

  ngOnInit() {
    this.createForm();

    this.loginForm.get('ldap').valueChanges.subscribe(v => {
      this.authStorageService.setLdap(v)
    })

    this.loginService.getSettings().subscribe((res) => {
      this.ldap = res.ldap;
      this.broker_name = res.broker_name
      if (res.sso) {
        this.sendSSO();
      }
    });
  }

  private createForm(): void {
    this.loginForm = this.fb.group({
      username: '' ,
      password: '',
      code: '',
      ldap: this.authStorageService.getLdapCheckbox()
    });
  }

  public get ldapToggleStatus(): boolean {
    return this.authStorageService.getLdapCheckbox();
  }

  private routePage(): void {
    if (this.authStorageService.checkLogin()) {
      this.route.navigate(['/pages']);
    } else {
      this.loaded = true;
    }
  }

  private sendSSO() {
    this.loginService.getSSO().subscribe(

      (res) => {
        this.authStorageService.saveInStorage(res.body.data);
        this.routePage();
      },

      (res) => {
        if (!res.status) {
          this.sendSSO();
        } else {
          this.routePage();
        }
      }
    );
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
