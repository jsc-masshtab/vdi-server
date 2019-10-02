import { WaitService } from './../../../common/components/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { UsersService } from '../all-users/users.service';
import { 
	FormBuilder, 
	FormGroup
} from '@angular/forms';


@Component({
  selector: 'vdi-add-user',
  templateUrl: './add-user.component.html'
})

export class AddUserComponent {

  public createUserForm: FormGroup;

  constructor(private service: UsersService,
              private dialogRef: MatDialogRef<AddUserComponent>,
              private fb: FormBuilder,
              private waitService: WaitService) {
                this.initForm();
              }


  public send() {
    this.waitService.setWait(true);
    this.service.createUser(this.createUserForm.value.username,this.createUserForm.value.password).subscribe(() => {
      this.service.getAllUsers().valueChanges.subscribe();
      this.dialogRef.close();
      this.waitService.setWait(false);
    });
  }

  private initForm(): void {
		this.createUserForm = this.fb.group({
			"username": "",
      "password": ""
		});
	}

}
