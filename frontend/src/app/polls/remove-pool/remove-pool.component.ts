import { PoolsService } from './../pools.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit } from '@angular/core';



@Component({
  selector: 'vdi-remove-pool',
  templateUrl: './remove-pool.component.html'
})

export class RemovePoolComponent implements OnInit {

  public pools: [];
  public defaultDataPools:string = "- Загрузка пулов виртуальных машин -";
  private deletePool:number;


  constructor(private service: PoolsService,
              private dialogRef: MatDialogRef<RemovePoolComponent>) {}

    
  ngOnInit() {
    this.getAllControllers();
  }

  public send() {
    this.service.removePool(this.deletePool).subscribe((res) => {
      if(res) {
        this.service.getAllPools().subscribe();
        this.dialogRef.close();
      }
    },(error) => {
      
    });
  }

  private getAllControllers() {
    this.defaultDataPools = "- Загрузка пулов виртуальных машин -";
    this.service.getAllPools()
      .subscribe((data) => {
        this.pools = data.map((item) => {
          return {
            'output': item.id,
            'input': item.name
          }
        });
        this.defaultDataPools = "- нет доступных пулов виртуальных машин -";
       
      },
      (error) => {
        this.defaultDataPools = "- нет доступных пулов виртуальных машин -";
      });
  }

  public selectValue(data) {
    this.deletePool = +data[0];
  }

}
