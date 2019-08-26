import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { UsersService } from '../users.service';
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
              private fb: FormBuilder) { this.initForm();}


  public send() {
    this.service.createUser(this.createUserForm.value.username,this.createUserForm.value.password).subscribe((res) => {
      this.service.getAllUsers().valueChanges.subscribe();
      this.dialogRef.close();
    },(error)=> {
    });
  }

  private initForm(): void {
		this.createUserForm = this.fb.group({
			"username": "",
      "password": ""
		});
	}

}
