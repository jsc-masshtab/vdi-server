import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { NodeDetailsComponent } from './node-details.component';
import { NodesService } from '../all-nodes/nodes.service';
import { of } from 'rxjs';

describe('NodeDetailsComponent', () => {
  let component: NodeDetailsComponent;
  let fixture: ComponentFixture<NodeDetailsComponent>;

  let serviceStub: Partial<NodesService>;

  beforeEach(async(() => {
    serviceStub = {
      getNode(): any {
        return {
          valueChanges: of({
            data: {
              node: {}
            }
          })
        };
      },
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ NodeDetailsComponent ],
      providers: [
        {
          provide: NodesService,
          useValue: serviceStub
        }
      ],
      schemas: [ CUSTOM_ELEMENTS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NodeDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
