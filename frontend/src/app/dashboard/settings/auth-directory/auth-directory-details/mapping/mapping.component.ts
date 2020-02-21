import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material';
import { Component, Inject, OnDestroy } from '@angular/core';
import { AuthenticationDirectoryService } from '../../auth-directory.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { takeUntil } from 'rxjs/operators';
import { Subject } from 'rxjs';


interface IData {
  id: string;
  priority: number;
  value_type: string;
  verbose_name: string;
  values: string[];
  description: string;
  assigned_groups: object[];
  idDirectory: string;
}

@Component({
  selector: 'vdi-mapping',
  templateUrl: './mapping.component.html'
})

export class MappingComponent implements OnDestroy {

  public form: FormGroup;
  public checkValid: boolean = false;
  private destroy: Subject<any> = new Subject<any>();

  private initForm(): void {
    this.form = this.fb.group({
      verbose_name: [this.data.verbose_name, Validators.required],
      description: this.data.description,
      value_type: this.data.value_type,
      groups: [this.data.assigned_groups, Validators.required],
      priority: this.data.priority,
      values: [this.data.values, Validators.required]
    });
  }

  constructor(private service: AuthenticationDirectoryService,
              private dialogRef: MatDialogRef<MappingComponent>,
              private fb: FormBuilder,
              private waitService: WaitService,
              @Inject(MAT_DIALOG_DATA) public data: IData) {
                this.initForm();
              }


  public compareFn(v1, v2): boolean {
    return v1 && v2 ? v1.id === v2.id : v1 === v2;
  }

  public send() {
    let value = {...this.form.value};
    let groupId = this.form.value.groups.map((group) => group.id);
    value.groups = groupId;
    this.checkValid = true;
    if (this.form.status === 'VALID') {
      this.waitService.setWait(true);
      this.service.updateMapping(value, this.data.idDirectory, this.data.id).subscribe(() => {
        this.service.getAuthenticationDirectory(this.data.idDirectory).pipe(takeUntil(this.destroy)).subscribe(() => {
          this.dialogRef.close();
          this.waitService.setWait(false);
        });
      });
    }
  }

  public delete() {
    this.waitService.setWait(true);
    this.service.deleteMapping(this.data.idDirectory, this.data.id).subscribe(() => {
    this.service.getAuthenticationDirectory(this.data.idDirectory).pipe(takeUntil(this.destroy)).subscribe(() => {
        this.dialogRef.close();
        this.waitService.setWait(false);
      });
    });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }
}





