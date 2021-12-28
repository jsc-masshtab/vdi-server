import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthStorageService } from '../../core/services/authStorage.service';
import { ISettings, LoginService } from '../../core/services/login.service';
import { ErrorsService } from '../../core/errors/errors.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'tc-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  public loginForm: FormGroup;
  public settings$: Observable<ISettings>;
  public useCode = new FormControl(false)

  constructor(
    private formBuilder: FormBuilder,
    private authStorageService: AuthStorageService,
    private loginService: LoginService,
    private errorsService: ErrorsService,
    private route: Router,
  ) { }

  ngOnInit(): void {
    if (this.authStorageService.checkLogin()) {
      this.route.navigate(['/pages']);
    }
    this.loginForm = this.formBuilder.group({
      username: '' ,
      password: '',
      code: '',
      ldap: this.authStorageService.getLdapCheckbox()
    });

    this.loginForm.get('ldap').valueChanges.subscribe(v => {
      this.authStorageService.setLdap(v)
    })
    this.settings$ = this.loginService.getSettings();

  }

  private routePage(): void {
    if (this.authStorageService.checkLogin()) {
      this.route.navigate(['/pages']);
    }
  }

  public get ldapToggleStatus(): boolean {
    return this.authStorageService.getLdapCheckbox();
  }
  
  public send() {
    this.loginService.auth(this.loginForm.value).subscribe((res: { data: { access_token: string, expires_on: string, username: string }} & { errors: [] } ) => {
      if (res && res.data) {
        this.authStorageService.saveInStorage(res.data);
        this.routePage();
      }

      if (res.errors !== undefined) {
        this.errorsService.setError(res.errors)
      }
    });
  }
}
