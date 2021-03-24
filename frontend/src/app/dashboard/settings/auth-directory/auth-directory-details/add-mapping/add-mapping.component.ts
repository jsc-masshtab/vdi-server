import { takeUntil, map } from 'rxjs/operators';
import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Component, OnInit, Inject, OnDestroy, } from '@angular/core';
import { AuthenticationDirectoryService } from '../../auth-directory.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject } from 'rxjs';

interface IData {
  id: string;
}


@Component({
  selector: 'vdi-add-mapping',
  templateUrl: './add-mapping.component.html'
})

export class AddMappingComponent implements OnInit, OnDestroy {

  public form: FormGroup;
  public checkValid: boolean = false;
  private destroy: Subject<any> = new Subject<any>();
  public pending = {
    groups: false
  };

  public groups: [] = [];


  private initForm(): void {
    this.form = this.fb.group({
      verbose_name: ['', Validators.required],
      description: '',
      value_type: ['', Validators.required],
      groups: ['', Validators.required],
      priority: ['', Validators.required],
      values: [[], Validators.required]
    });
  }

  constructor(private service: AuthenticationDirectoryService,
              private dialogRef: MatDialogRef<AddMappingComponent>,
              private fb: FormBuilder,
              private waitService: WaitService,
              @Inject(MAT_DIALOG_DATA) public data: IData) {
                this.initForm();
              }

  ngOnInit() {
    this.getGroups();
  }

  public send() {
    this.checkValid = true;
    if (this.form.status === 'VALID') {
      this.waitService.setWait(true);
      this.service.addAuthDirMapping(this.form.value, this.data.id).pipe(takeUntil(this.destroy)).subscribe(() => {
        this.service.getAuthenticationDirectory(this.data.id).valueChanges.pipe(map(data => data.data)).subscribe(() => {
          this.dialogRef.close();
          this.waitService.setWait(false);
        });
      });
    }
  }

  private getGroups(): void  {
    this.pending.groups = true;
    this.service.getGroups().valueChanges.pipe(takeUntil(this.destroy))
    .subscribe( (data) => {
      this.groups = data.data['groups'];
      this.pending.groups = false;
    });
  }

  public addValue(value) {
    let arr = [...this.form.value.values];
    arr.push(value);
    if (value && !this.form.value.values.includes(value)) {
      this.form.get('values').setValue(arr);
    }
  }


  ngOnDestroy() {
    this.destroy.next(null);
  }


}





