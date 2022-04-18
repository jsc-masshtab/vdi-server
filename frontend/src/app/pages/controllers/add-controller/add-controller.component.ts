import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { Subscription } from 'rxjs';

import { WaitService } from '../../../core/components/wait/wait.service';
import { ControllersService } from '../all-controllers/controllers.service';



@Component({
  selector: 'vdi-add-controller',
  templateUrl: './add-controller.component.html'
})

export class AddControllerComponent implements OnInit, OnDestroy {

  public createForm: FormGroup;
  private sub: Subscription;
  public checkValid: boolean = false;

  constructor(private service: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddControllerComponent>,
              private fb: FormBuilder) { }


  ngOnInit() {
    this.createFormAddPool();
  }

  private createFormAddPool(): void {
    this.createForm = this.fb.group({
      address: ['', Validators.required],
      verbose_name: ['', Validators.required],
      description: '',
      token: ''
    });
  }

  public send() {
    this.checkValid = true;
    if (this.createForm.status === 'VALID') {
      this.waitService.setWait(true);
      this.service.addController(this.createForm.value).subscribe((res) => {
        if (res) {
          this.sub = this.service.getAllControllers().valueChanges.subscribe(() => {
            this.waitService.setWait(false);
            this.dialogRef.close();
          });
        }
        
      });
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
