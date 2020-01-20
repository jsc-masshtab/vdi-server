import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { AuthenticationDirectoryService } from '../auth-directory.service';
import { FormBuilder, FormGroup } from '@angular/forms';


@Component({
  selector: 'vdi-add-auth-directory',
  templateUrl: './add-auth-directory.component.html'
})

export class AddAuthenticationDirectoryComponent {

  public form: FormGroup;

  private initForm(): void {
    this.form = this.fb.group({
      domain_name: '',
      verbose_name: '',
      directory_url: 'ldap://',
      description: '',
      /* connection_type: 'LDAP',
      directory_type: 'ActiveDirectory',
      service_username: '',
      service_password: '',
      admin_server: '',
      subdomain_name: '',
      kdc_urls: [[]],
      sso: false, */
    });
  }

  constructor(private service: AuthenticationDirectoryService,
              private dialogRef: MatDialogRef<AddAuthenticationDirectoryComponent>,
              private fb: FormBuilder,
              private waitService: WaitService) {
                this.initForm();
              }

  public send() {
    this.waitService.setWait(true);
    this.service.createAuthDir({ ...this.form.value }).subscribe(() => {
      this.service.getAllAuthenticationDirectory().refetch();
      this.dialogRef.close();
      this.waitService.setWait(false);
    });
  }
}
