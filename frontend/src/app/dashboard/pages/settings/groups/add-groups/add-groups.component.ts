import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material/dialog';
import { Component, OnDestroy } from '@angular/core';
import { GroupsService } from '../groups.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subscription } from 'rxjs';


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

