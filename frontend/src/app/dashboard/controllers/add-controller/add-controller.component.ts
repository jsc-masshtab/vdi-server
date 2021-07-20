import { Subscription } from 'rxjs';
import { WaitService } from '../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material/dialog';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ControllersService } from '../all-controllers/controllers.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';


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
      }, er => {
          console.log(er)
      });
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
