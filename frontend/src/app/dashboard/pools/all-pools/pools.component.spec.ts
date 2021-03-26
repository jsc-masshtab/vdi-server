import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { PoolsComponent } from './pools.component';
import { PoolsService } from './pools.service';

describe('PoolsComponent', () => {

  let component: PoolsComponent;
  let fixture: ComponentFixture<PoolsComponent>;

  let serviceStub: Partial<PoolsService>;
  let dialogStub: Partial<MatDialog>;

  beforeEach(async(() => {
    serviceStub = {
      getAllControllers(): any {
        return {
          valueChanges: of({
            data: {
              controllers: []
            }
          })
        }
      },
      getAllPools(): any {
        return {
          valueChanges: of({
            data: {
              pools: []
            }
          })
        }
      },
      paramsForGetPools: {
        spin: false
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ PoolsComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: dialogStub
        },
        {
          provide: PoolsService,
          useValue: serviceStub
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PoolsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
