import { MatDialogRef } from '@angular/material';
import { Component, OnInit } from '@angular/core';
import { PoolsService } from './../polls.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-pool-add',
  templateUrl: './pool-add.component.html'
})

export class PoolAddComponent implements OnInit {

  public dataSelect: object[];
  private tmId: string;
  public poolName:string;

  constructor(private poolsService: PoolsService,
              private dialogRef: MatDialogRef<PoolAddComponent>) {
  }

  ngOnInit() {
    this.getTemplate();
  }

  private getTemplate() {
    this.poolsService.getAllTemplates().valueChanges.pipe(map(data => data.data.templates)).subscribe((res)=> {
      this.dataSelect= res.map((item) => {
        return {
          'output': item.id,
          'input': item.name
        }
      })
    });
  }

  private selectValue(data) {
    this.tmId = data[0];
  }

  public send() {
    this.poolsService.createPoll(this.poolName,this.tmId).subscribe((res) => {
      if(res) {
        this.poolsService.getAllPools().valueChanges.subscribe();
        this.dialogRef.close();
      }
    });
  }

}
