import { WaitService } from './../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit } from '@angular/core';
import { ControllersService } from '../all-controllers/controllers.service';
import { FormBuilder, FormGroup } from '@angular/forms';


@Component({
  selector: 'vdi-add-controller',
  templateUrl: './add-controller.component.html'
})

export class AddControllerComponent implements OnInit {

  public createForm: FormGroup;

  constructor(private service: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddControllerComponent>,
              private fb: FormBuilder) { }


  ngOnInit() {
    this.createFormAddPool();
  }

  private createFormAddPool(): void {
    this.createForm = this.fb.group({
      address: '',
      username: '',
      verbose_name: '',
      password: '',
      description: ''
    });
  }

  public send() {
    this.waitService.setWait(true);
    this.service.addController(this.createForm.value).subscribe(() => {
      this.service.getAllControllers().valueChanges.subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
    });
  }
}
