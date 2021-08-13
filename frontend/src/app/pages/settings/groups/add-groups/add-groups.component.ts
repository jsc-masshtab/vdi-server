import { Component, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { Subscription } from 'rxjs';

import { WaitService } from '../../../../core/components/wait/wait.service';
import { GroupsService } from '../groups.service';


@Component({
  selector: 'vdi-add-groups',
  templateUrl: './add-groups.component.html'
})

export class AddGroupComponent implements OnDestroy {

  public form: FormGroup;
  public checkValid: boolean = false;
  private sub: Subscription;

  private initForm(): void {
    this.form = this.fb.group({
      verbose_name: ['', Validators.required],
      description: ''
    });
  }

  constructor(private service: GroupsService,
              private dialogRef: MatDialogRef<AddGroupComponent>,
              private fb: FormBuilder,
              private waitService: WaitService) {
                this.initForm();
              }


  public send() {
    this.checkValid = true;
    if (this.form.status === 'VALID') {
      this.waitService.setWait(true);
      this.service.createGroup(this.form.value).subscribe((res) => {
        if (res) {
          this.sub =  this.service.getGroups().valueChanges.subscribe(() => {
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

