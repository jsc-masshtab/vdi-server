import { ErrorsService } from './../../../common/components/errors/errors.service';
import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { ControllersService } from '../controllers.service';


@Component({
  selector: 'vdi-add-controller',
  templateUrl: './add-controller.component.html'
})

export class AddControllerComponent {

  public controller: string = "";
  public description: string = "";


  constructor(private service: ControllersService,
              private dialogRef: MatDialogRef<AddControllerComponent>,
              private j: ErrorsService) {}


  public send() {
    this.service.addController(this.controller,this.description).subscribe((res) => {
      this.service.getAllControllers().valueChanges.subscribe();
      this.dialogRef.close();
    },(error)=> {
      this.j.setError( [{
        message: '1',
      },{
        message: '2',
      }]);
    });

    // setTimeout(() => {
    //   this.j.setError( [{
    //     message: '3',
    //   },{
    //     message: '4',
    //   }]);
    // },3000);
  }

}
