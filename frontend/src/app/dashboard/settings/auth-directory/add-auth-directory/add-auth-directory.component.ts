import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { AuthenticationDirectoryService } from '../auth-directory.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';


@Component({
  selector: 'vdi-add-auth-directory',
  templateUrl: './add-auth-directory.component.html'
})

export class AddAuthenticationDirectoryComponent {

  public form: FormGroup;
  public checkValid: boolean = false;

  private initForm(): void {
    this.form = this.fb.group({
      domain_name: ['', Validators.required],
      verbose_name: ['', Validators.required],
      directory_url: ['ldap://', [Validators.required, Validators.pattern(/^ldap[s]?:\/\/[a-zA-Z0-9.-_+ ]+$/)]],
      description: '',
      service_username: '',
      service_password: '',
      /* connection_type: 'LDAP',
      directory_type: 'ActiveDirectory',
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
    this.checkValid = true;
    if (this.form.status === 'VALID') {
      this.waitService.setWait(true);

      this.service.createAuthDir({ ...this.form.value }).subscribe(() => {
        this.service.getAllAuthenticationDirectory().refetch();
        this.dialogRef.close();
        this.waitService.setWait(false);
      });
    }
  }
}

