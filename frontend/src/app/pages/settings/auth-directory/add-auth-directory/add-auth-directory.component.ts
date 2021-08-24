import { Component, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { Subscription } from 'rxjs';

import { WaitService } from '@core/components/wait/wait.service';
import { AuthenticationDirectoryService } from '../auth-directory.service';


@Component({
  selector: 'vdi-add-auth-directory',
  templateUrl: './add-auth-directory.component.html'
})

export class AddAuthenticationDirectoryComponent implements OnDestroy {

  private sub: Subscription;

  public form: FormGroup;
  public checkValid: boolean = false;

  private initForm(): void {
    this.form = this.fb.group({
      domain_name: ['', Validators.required],
      dc_str: ['', Validators.required],
      verbose_name: ['', Validators.required],
      directory_url: ['', [Validators.required, Validators.pattern(/^ldap[s]?:\/\/[a-zA-Z0-9.-_+ ]+$/)]],
      directory_type: 'ActiveDirectory',
      description: '',
      service_username: '',
      service_password: '',
    });

    this.sub = this.form.get('directory_url').valueChanges.subscribe((directory_url) => {
      if (!String(directory_url).match(/^ldap[s]?:\/\//)) {
        this.form.get('directory_url').setValue(`ldap://${directory_url}`)
      }
    })
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

  ngOnDestroy() {
    this.sub.unsubscribe()
  }
}

