import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { UsersService } from '../users.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';


@Component({
  selector: 'vdi-add-user',
  templateUrl: './add-user.component.html'
})

export class AddUserComponent {

  public form: FormGroup;
  public checkValid: boolean = false;

  private initForm(): void {
    this.form = this.fb.group({
      username: ['', [Validators.required, Validators.pattern(/^[a-zA-Z0-9-.+]{3,128}$/)]],
      password: ['', [Validators.required, Validators.pattern(/^.+$/)]],
      email: ['', [Validators.required, Validators.pattern(/^[a-zA-Z0-9.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+$/)]],
      first_name: ['', [Validators.required, Validators.pattern(/^[a-zA-Zа-яА-ЯёЁ-]{1,32}$/)]],
      last_name: ['', [Validators.required, Validators.pattern(/^[a-zA-Zа-яА-ЯёЁ-]{1,128}$/)]],
      is_superuser: false
    });
  }

  constructor(private service: UsersService,
              private dialogRef: MatDialogRef<AddUserComponent>,
              private fb: FormBuilder,
              private waitService: WaitService) {
                this.initForm();
              }


  public send() {
    this.checkValid = true;
    if (this.form.status === 'VALID') {
      this.waitService.setWait(true);
      this.service.createUser({ ...this.form.value }).subscribe(() => {
        this.service.getAllUsers().valueChanges.subscribe();
        this.dialogRef.close();
        this.waitService.setWait(false);
      });
    }
  }
}
